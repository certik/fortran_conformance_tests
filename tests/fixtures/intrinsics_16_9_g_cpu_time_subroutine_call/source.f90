program i169g_cpu_time_subroutine_call
  implicit none
  real :: t
  t = -10.0
  call cpu_time(t)
  call require_true('cpu_time assigned available value', t >= 0.0)
  write(*,'(a)') 'INTRINSICS 16.9.G CPU TIME SUBROUTINE CALL OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_cpu_time_subroutine_call
