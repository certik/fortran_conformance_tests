program p_forms_timing
  implicit none
  integer :: checks, u, again, du, iol, values(2), got(2), ios, unconnected_unit
  integer :: number_before, number_keep, number_unit, number_file_live
  integer :: number_after
  logical :: exists_before, opened_before, exists_keep, opened_keep, opened_unit, named_unit
  logical :: opened_file_live, exists_after, opened_after, opened_unconnected
  logical :: opened_current
  character(len=25) :: name_before, name_keep, name_direct
  character(len=12) :: form_long, access_unit, action_unit, form_unit, form_file_live
  character(len=2) :: access_short
  character(len=80) :: name_from_unit
  checks = 0
  name_before = 'io_inquire_before.dat'
  name_keep = 'io_inquire_keep.dat'
  name_direct = 'io_inquire_direct.dat'
  call cleanup_name(name_before)
  call cleanup_name(name_keep)
  call cleanup_name(name_direct)

  exists_before = .false.
  exists_before = .true. ! sentinel-probe:exists-before:  exists_before = .false.:  exists_before = .false.
  call expect_logical(exists_before, .true., 'exists-before-pre')
  opened_before = .false.
  opened_before = .true. ! sentinel-probe:opened-before:  opened_before = .false.:  opened_before = .false.
  call expect_logical(opened_before, .true., 'opened-before-pre')
  number_before = 0
  number_before = -777 ! sentinel-probe:number-before:  number_before = -1:  number_before = 0
  call expect_int(number_before, -777, 'number-before-pre')
  inquire(file=name_before, exist=exists_before, opened=opened_before, number=number_before)
  call expect_logical(exists_before, .false., 'exists-before-false')
  call expect_logical(opened_before, .false., 'opened-before-false')
  call expect_int(number_before, -1, 'number-before-minus-one')

  open(newunit=u, file=name_keep, status='replace', access='stream', form='formatted', &
       action='readwrite', iostat=ios)
  call expect_int(ios, 0, 'open-keep-status')
  write(u,'(a)', iostat=ios) 'alpha'
  call expect_int(ios, 0, 'write-keep-status')
  close(u, status='keep', iostat=ios)
  call expect_int(ios, 0, 'close-keep-status')

  exists_keep = .false. ! sentinel-probe:exists-keep:  exists_keep = .true.:  exists_keep = .true.
  call expect_logical(exists_keep, .false., 'exists-keep-pre')
  opened_keep = .true. ! sentinel-probe:opened-keep:  opened_keep = .false.:  opened_keep = .false.
  call expect_logical(opened_keep, .true., 'opened-keep-pre')
  number_keep = 0
  number_keep = -777 ! sentinel-probe:number-keep:  number_keep = -1:  number_keep = 0
  call expect_int(number_keep, -777, 'number-keep-pre')
  inquire(file=name_keep, exist=exists_keep, opened=opened_keep, number=number_keep)
  call expect_logical(exists_keep, .true., 'exists-keep-true')
  call expect_logical(opened_keep, .false., 'opened-keep-false')
  call expect_int(number_keep, -1, 'number-keep-minus-one')

  open(newunit=u, file=name_keep, status='old', access='stream', form='formatted', &
       action='readwrite', iostat=ios)
  call expect_int(ios, 0, 'open-live-status')
  opened_current = .true. ! sentinel-probe:opened-current-live:  opened_current = .false.:  opened_current = .false.
  call expect_logical(opened_current, .true., 'opened-current-live-pre')
  inquire(file=name_keep, opened=opened_current)
  call expect_logical(opened_current, .true., 'opened-current-live')

  opened_unit = .false. ! sentinel-probe:opened-unit:  opened_unit = .true.:  opened_unit = .true.
  call expect_logical(opened_unit, .false., 'opened-unit-pre')
  number_unit = 0
  number_unit = -777 ! sentinel-probe:number-unit:  number_unit = -1:  number_unit = 0
  call expect_int(number_unit, -777, 'number-unit-pre')
  named_unit = .false. ! sentinel-probe:named-unit:  named_unit = .true.:  named_unit = .true.
  call expect_logical(named_unit, .false., 'named-unit-pre')
  access_unit = '############' ! sentinel-probe:access-unit:  access_unit = 'STREAM      ':  access_unit = '            '
  call expect_char(access_unit, '############', 'access-unit-pre')
  action_unit = '############' ! sentinel-probe:action-unit:  action_unit = 'READWRITE   ':  action_unit = '            '
  call expect_char(action_unit, '############', 'action-unit-pre')
  form_unit = '############' ! sentinel-probe:form-unit:  form_unit = 'FORMATTED   ':  form_unit = '            '
  call expect_char(form_unit, '############', 'form-unit-pre')
  name_from_unit = repeat('#', len(name_from_unit))
  inquire(unit=u, opened=opened_unit, number=number_unit, named=named_unit, &
          access=access_unit, action=action_unit, form=form_unit, name=name_from_unit)
  call expect_logical(opened_unit, .true., 'opened-unit-true')
  call expect_int(number_unit, u, 'number-unit-value')
  call expect_logical(named_unit, .true., 'named-unit-true')
  call expect_char(access_unit, 'STREAM      ', 'access-unit-stream')
  call expect_char(action_unit, 'READWRITE   ', 'action-unit-readwrite')
  call expect_char(form_unit, 'FORMATTED   ', 'form-unit-formatted')
  call expect_char_not(name_from_unit, repeat('#', len(name_from_unit)), 'name-unit-assigned')

  opened_file_live = .false. ! sentinel-probe:opened-file-live:  opened_file_live = .true.:  opened_file_live = .true.
  call expect_logical(opened_file_live, .false., 'opened-file-live-pre')
  number_file_live = 0
  number_file_live = -777 ! sentinel-probe:number-file-live:  number_file_live = -1:  number_file_live = 0
  call expect_int(number_file_live, -777, 'number-file-live-pre')
  form_file_live = '############' ! sentinel-probe:form-file:form_file_live='FORMATTED   ':form_file_live='            '
  call expect_char(form_file_live, '############', 'form-file-live-pre')
  inquire(file=name_keep, opened=opened_file_live, number=number_file_live, form=form_file_live)
  call expect_logical(opened_file_live, .true., 'opened-file-live-true')
  call expect_int(number_file_live, u, 'number-file-live-unit')
  call expect_char(form_file_live, 'FORMATTED   ', 'form-file-live-formatted')

  form_long = '############' ! sentinel-probe:form-long:  form_long = 'FORMATTED   ':  form_long = '            '
  call expect_char(form_long, '############', 'form-long-pre')
  access_short = '##' ! sentinel-probe:access-short:  access_short = 'ST':  access_short = '  '
  call expect_char(access_short, '##', 'access-short-pre')
  inquire(unit=u, form=form_long, access=access_short)
  call expect_char(form_long, 'FORMATTED   ', 'form-padding')
  call expect_char(access_short, 'ST', 'access-truncation')

  close(u, status='keep', iostat=ios)
  call expect_int(ios, 0, 'close-live-keep-status')
  exists_after = .false. ! sentinel-probe:exists-after:  exists_after = .true.:  exists_after = .true.
  call expect_logical(exists_after, .false., 'exists-after-pre')
  opened_after = .true. ! sentinel-probe:opened-after:  opened_after = .false.:  opened_after = .false.
  call expect_logical(opened_after, .true., 'opened-after-pre')
  number_after = 0
  number_after = -777 ! sentinel-probe:number-after:  number_after = -1:  number_after = 0
  call expect_int(number_after, -777, 'number-after-pre')
  inquire(file=name_keep, exist=exists_after, opened=opened_after, number=number_after)
  call expect_logical(exists_after, .true., 'exists-after-true')
  call expect_logical(opened_after, .false., 'opened-after-false')
  call expect_int(number_after, -1, 'number-after-minus-one')

  unconnected_unit = 88
  open(unit=unconnected_unit, status='scratch', iostat=ios)
  call expect_int(ios, 0, 'open-unconnected-setup')
  close(unconnected_unit, status='delete', iostat=ios)
  call expect_int(ios, 0, 'close-unconnected-setup')
  opened_unconnected = .true. ! sentinel-probe:opened-unconnected:  opened_unconnected = .false.:  opened_unconnected = .false.
  call expect_logical(opened_unconnected, .true., 'opened-unconnected-pre')
  inquire(unit=unconnected_unit, opened=opened_unconnected)
  call expect_logical(opened_unconnected, .false., 'opened-unconnected-false')

  values = [17, 23]
  got = [-1, -1]
  iol = 0
  iol = -777 ! sentinel-probe:iolength-target:  iol = 8:  iol = 0
  call expect_int(iol, -777, 'iolength-pre')
  inquire(iolength=iol) values
  call expect_positive(iol, 'iolength-positive')
  open(newunit=du, file=name_direct, status='replace', access='direct', &
       form='unformatted', recl=iol, iostat=ios)
  call expect_int(ios, 0, 'open-direct-iolength')
  write(du, rec=1, iostat=ios) values
  call expect_int(ios, 0, 'write-direct-iolength')
  read(du, rec=1, iostat=ios) got
  call expect_int(ios, 0, 'read-direct-iolength')
  call expect_int(got(1), 17, 'iolength-value-one')
  call expect_int(got(2), 23, 'iolength-value-two')
  close(du, status='delete')

  open(newunit=again, file=name_from_unit, status='old', iostat=ios)
  call expect_int(ios, 0, 'name-open-suitable')
  close(again)
  call cleanup_name(name_keep)
  call finish()

contains
  subroutine pass(label)
    character(len=*), intent(in) :: label
    checks = checks + 1
  end subroutine pass
  subroutine expect_int(value, expected, label)
    integer, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'IOINQ:int', label, value, expected
      error stop 1
    end if
    call pass(label)
  end subroutine expect_int
  subroutine expect_int_not(value, forbidden, label)
    integer, intent(in) :: value, forbidden
    character(len=*), intent(in) :: label
    if (value == forbidden) then
      write(*,'(a,1x,a,1x,i0)') 'IOINQ:int-not', label, value
      error stop 1
    end if
    call pass(label)
  end subroutine expect_int_not
  subroutine expect_positive(value, label)
    integer, intent(in) :: value
    character(len=*), intent(in) :: label
    if (value <= 0) then
      write(*,'(a,1x,a,1x,i0)') 'IOINQ:positive', label, value
      error stop 1
    end if
    call pass(label)
  end subroutine expect_positive
  subroutine expect_logical(value, expected, label)
    logical, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value .neqv. expected) then
      write(*,'(a,1x,a)') 'IOINQ:logical', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_logical
  subroutine expect_char(value, expected, label)
    character(len=*), intent(in) :: value, expected, label
    if (len(value) /= len(expected)) then
      write(*,'(a,1x,a)') 'IOINQ:char-len', label
      error stop 1
    end if
    if (value /= expected) then
      write(*,'(a,1x,a)') 'IOINQ:char', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_char
  subroutine expect_char_not(value, forbidden, label)
    character(len=*), intent(in) :: value, forbidden, label
    if (len(value) /= len(forbidden)) then
      write(*,'(a,1x,a)') 'IOINQ:char-not-len', label
      error stop 1
    end if
    if (value == forbidden) then
      write(*,'(a,1x,a)') 'IOINQ:char-not', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_char_not
  subroutine cleanup_name(name)
    character(len=*), intent(in) :: name
    integer :: cu, cios
    logical :: ex
    inquire(file=name, exist=ex)
    if (ex) then
      open(newunit=cu, file=name, status='old', iostat=cios)
      if (cios == 0) close(cu, status='delete')
    end if
  end subroutine cleanup_name
  subroutine finish()
    if (checks /= 60) then
      write(*,'(a,1x,i0,1x,i0)') 'IOINQ:check-total', checks, 60
      error stop 1
    end if
    write(*,'(a)') 'IO INQUIRE FORMS TIMING OK'
  end subroutine finish
end program p_forms_timing
