program i169g_date_and_time_zone_digits
  implicit none
  character(len=5) :: zone_value, zone_sink
  zone_value = '#####'
  zone_sink = '!!!!!'
  call date_and_time(zone=zone_value)
  call require_true('zone sign and digits', &
       len(zone_value) == 5 .and. &
       (zone_value(1:1) == '+' .or. zone_value(1:1) == '-') .and. &
       verify(zone_value(2:5), '0123456789') == 0)
  write(*,'(a)') 'INTRINSICS 16.9.G DATE AND TIME ZONE DIGITS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_date_and_time_zone_digits
