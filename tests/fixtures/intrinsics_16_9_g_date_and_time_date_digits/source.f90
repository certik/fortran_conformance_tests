program i169g_date_and_time_date_digits
  implicit none
  character(len=8) :: date_value, date_sink
  integer :: month, day
  date_value = '########'
  date_sink = '!!!!!!!!'
  call date_and_time(date_value)
  month = decimal2(date_value(5:6))
  day = decimal2(date_value(7:8))
  call require_true('date has eight digits', len(date_value) == 8 .and. all_digits(date_value))
  call require_true('date month day positions', month >= 1 .and. month <= 12 .and. day >= 1 .and. day <= 31)
  write(*,'(a)') 'INTRINSICS 16.9.G DATE AND TIME DATE DIGITS OK'
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
end program i169g_date_and_time_date_digits
