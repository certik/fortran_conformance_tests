program i169g_date_and_time_subroutine_call
  implicit none
  character(len=8) :: date_value
  date_value = '########'
  call date_and_time(date=date_value)
  call require_true('subroutine call assigned date', verify(date_value, '0123456789') == 0)
  write(*,'(a)') 'INTRINSICS 16.9.G DATE AND TIME SUBROUTINE CALL OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_date_and_time_subroutine_call
