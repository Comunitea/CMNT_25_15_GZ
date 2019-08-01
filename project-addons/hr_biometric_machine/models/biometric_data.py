# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import api, fields, models

import datetime
import pytz

import logging
_logger = logging.getLogger(__name__)

class BiometricData(models.Model):
    _name = 'biometric.data'

    # Order records by date to assure will be crated
    # first the oldest registers
    _order = 'datetime'

    @api.one
    def _compute_get_employee_id(self):
        if self.biometric_user_id.employee_id:
            self.employee_id = self.biometric_user_id.employee_id

    @api.one
    def _compute_get_name(self):
        if self.biometric_user_id:
            self.name = self.biometric_user_id.name

    datetime = fields.Datetime('Date')
    biometric_user_id = fields.Many2one(
        'biometric.user', 'Related biometric user',)
    employee_id = fields.Many2one(
        'hr.employee', 'Related employee', compute=_compute_get_employee_id,)
    name = fields.Char(
        'Employee name in biometric device',
        compute=_compute_get_name,)
    action_perform = fields.Char('Action perform')

    @api.model
    def create_hr_attendace(
            self, employee_id, date, action_perform,
            biometric_id, state='right',):
        """
        Register have to be always: sign_in, sign_out, sign_in and so on
        In hr_attedance moules there is a a contrain
        which assures never a sign_in or a sign_out are next to the same kind
        of regiter, this means register are followed are wrong
            sign_out, sign_in, sign_in  --> because there are next to two sign_in
            sign_out, sign_out, sign_in  --> because there are next to two sign_out
        User could forget to sign incoming and outcoming regiters a lot of times
        This function assures that regardless contrain continue being true
        """
        hr_attendance_obj = self.env['hr.attendance']
        biometric_machine_obj = self.env['biometric.machine']
        biometric_machine = biometric_machine_obj.browse(biometric_id)

        mode = biometric_machine.mode

        def convert_date_to_utc(date):
            local = pytz.timezone(
                biometric_machine.timezone,)
            date = local.localize(date, is_dst=None)
            date = date.astimezone(pytz.utc)
            date.strftime('%Y-%m-%d: %H:%M:%S')
            return date.replace(tzinfo=None)

        def convert_from_local_to_utc(date):
            local = pytz.timezone(
                biometric_machine.timezone,)
            date = date.replace(tzinfo=pytz.utc)
            date = date.astimezone(local)
            date.strftime('%Y-%m-%d: %H:%M:%S')
            return date.replace(tzinfo=None)

        # Get the max time of working set up for the device
        max_time = biometric_machine.max_time
        min_time = biometric_machine.min_time
        # Get a delta time of 1 minute
        delta_1_sec = datetime.timedelta(seconds=1)
        # Get previous attendace
        prev_att = hr_attendance_obj.search(
            [('employee_id', '=', employee_id),
             ('name', '<', convert_date_to_utc(date).isoformat()),
             ('action', 'in', ('sign_in', 'sign_out'),), ],
            limit=1, order='name DESC',)
        # Get date of the last user register
        if not prev_att:
            last_date = date
        else:
            last_date = datetime.datetime.strptime(
                prev_att.name, '%Y-%m-%d %H:%M:%S',)

        # Si la diferencia con el último registro es menor que el tiempo mínimo
        # no creo registro de asistencia
        last_date = convert_from_local_to_utc(last_date)
        if abs(last_date - date) < min_time:
            return

        if mode == 'auto':
            action_perform = 'sign_in'
            if prev_att and prev_att.action == 'sign_in':
                action_perform = 'sign_out'

        # Modo manual, puede que cree fix
        elif prev_att and prev_att.action == action_perform:
            sign_state = \
                'sign_in' if prev_att.action == 'sign_out' else 'sign_out'
            if abs(last_date - date) >= max_time:
                new_time = last_date + max_time
            else:
                new_time = last_date + delta_1_sec
            self.create_hr_attendace(employee_id, new_time, sign_state,
                                     biometric_id, state='fix')

        # Convert date using correct timezone
        date = convert_date_to_utc(date)
        self._create_hr_attendace(employee_id, date, action_perform, state,
                                biometric_machine)

    @api.model
    def _create_hr_attendace(
            self, employee_id, date, action_perform, state, biometric_machine):
        hr_attendance_obj = self.env['hr.attendance']
        hr_attendance_obj.create({
            'employee_id': employee_id,
            'name': date.strftime('%Y-%m-%d: %H:%M:%S'),
            'action': action_perform,
            'state': state, 
            'latitude': biometric_machine.latitude, 
            'longitude': biometric_machine.longitude, 
        })

    @classmethod
    def convert_to_hr_attendance_classmethod(
            cls, biometric_data, biometric_data_obj,):
        for datum in biometric_data:
            if not datum.employee_id:
                continue
            date = datetime.datetime.strptime(
                datum.datetime, '%Y-%m-%d %H:%M:%S',)
            biometric_data_obj.create_hr_attendace(
                datum.employee_id.id, date,
                datum.action_perform,
                datum.biometric_user_id.biometric_device.id,
            )
            datum.unlink()

    @classmethod
    def import_data_classmethod(
            cls, biometric_machine, biometric_data_obj, biometric_user_obj,):
        attendances = biometric_machine.getattendance()
        for user_attendances in attendances:
            # Sorted elements using timestamp
            user_attendances.sort(key=lambda x: x.timestamp)
            user = biometric_user_obj.search([
                    ['biometric_id', '=', int(
                        user_attendances[0].user_id), ], ], )
            for attendance in user_attendances:
                if not attendance.action_perform:
                    continue
                elif not user.employee_id:
                    biometric_data_obj.create(
                        {'biometric_user_id': user.id,
                         'datetime': attendance.timestamp,
                         'action_perform': attendance.action_perform, }, )
                else:
                    biometric_data_obj.create_hr_attendace(
                        user.employee_id.id, attendance.timestamp,
                        attendance.action_perform,
                        user.biometric_device.id,)
        biometric_machine.clean_attendance()

    @api.model
    def convert_to_hr_attendance(self):
        biometric_data = self.search([])
        self.convert_to_hr_attendance_classmethod(
            biometric_data, self,)

    @api.model
    def import_data(self):
        biometric_machine_obj = self.env['biometric.machine']
        biometric_user_obj = self.env['biometric.user']
        # First of all convert the oldest registers
        # into hr.attendance registers
        try:
            self.convert_to_hr_attendance()
            biometric_machines = biometric_machine_obj.search([])
            for biometric_machine in biometric_machines:
                self.import_data_classmethod(
                    biometric_machine, self, biometric_user_obj,)
        except:
            _logger.error("Error Importing attendances from cron")
