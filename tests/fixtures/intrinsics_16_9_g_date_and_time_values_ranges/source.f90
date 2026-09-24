program i169g_date_and_time_values_ranges
  implicit none
  integer :: date_values(8), time_values(8), zone_values(8), values_sink(8)
  integer :: zone_minutes
  character(len=5) :: zone_value
  date_values = 123456789
  time_values = 123456789
  zone_values = 123456789
  values_sink = 123456789
  zone_value = '#####'
  call date_and_time(values=date_values)
  call require_true('values date fields available and ranged', &
       date_values(1) /= -huge(date_values(1)) .and. &
       date_values(2) >= 1 .and. date_values(2) <= 12 .and. &
       date_values(3) >= 1 .and. date_values(3) <= 31)
  call date_and_time(values=time_values)
  call require_true('values time fields available and ranged', &
       all(time_values(5:8) /= -huge(time_values(1))) .and. &
       time_values(5) >= 0 .and. time_values(5) <= 23 .and. &
       time_values(6) >= 0 .and. time_values(6) <= 59 .and. &
       time_values(7) >= 0 .and. time_values(7) <= 60 .and. &
       time_values(8) >= 0 .and. time_values(8) <= 999)
  call date_and_time(zone=zone_value, values=zone_values)
  zone_minutes = 60 * decimal2(zone_value(2:3)) + decimal2(zone_value(4:5))
  if (zone_value(1:1) == '-') zone_minutes = -zone_minutes
  call require_true('values zone agrees with zone argument', &
       zone_values(4) /= -huge(zone_values(1)) .and. zone_values(4) == zone_minutes)
  write(*,'(a)') 'INTRINSICS 16.9.G DATE AND TIME VALUES RANGES OK'
contains
  logical function all_digits(s)
    character(len=*), intent(in) :: s
    all_digits = verify(s, '0123456789') == 0
  end function all_digits
  integer function digit_value(c)
    character(len=1), intent(in) :: c
    digit_value = index('0123456789', c) - 1
  end function digit_value
  integer function decimal2(s)
    character(len=*), intent(in) :: s
    decimal2 = 10 * digit_value(s(1:1)) + digit_value(s(2:2))
  end function decimal2
  integer function decimal3(s)
    character(len=*), intent(in) :: s
    decimal3 = 100 * digit_value(s(1:1)) + 10 * digit_value(s(2:2)) + digit_value(s(3:3))
  end function decimal3
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_date_and_time_values_ranges
