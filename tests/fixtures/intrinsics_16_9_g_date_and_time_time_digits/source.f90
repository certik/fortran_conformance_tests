program i169g_date_and_time_time_digits
  implicit none
  character(len=10) :: time_value, time_sink
  integer :: hour, minute, second, millis
  time_value = '##########'
  time_sink = '!!!!!!!!!!'
  call date_and_time(time=time_value)
  hour = decimal2(time_value(1:2))
  minute = decimal2(time_value(3:4))
  second = decimal2(time_value(5:6))
  millis = decimal3(time_value(8:10))
  call require_true('time digits and decimal point', &
       len(time_value) == 10 .and. time_value(7:7) == '.' .and. &
       all_digits(time_value(1:6)//time_value(8:10)))
  call require_true('time fields in source ranges', &
       hour >= 0 .and. hour <= 23 .and. minute >= 0 .and. minute <= 59 .and. &
       second >= 0 .and. second <= 60 .and. millis >= 0 .and. millis <= 999)
  write(*,'(a)') 'INTRINSICS 16.9.G DATE AND TIME TIME DIGITS OK'
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
end program i169g_date_and_time_time_digits
