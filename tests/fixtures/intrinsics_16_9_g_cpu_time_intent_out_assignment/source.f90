program i169g_cpu_time_intent_out_assignment
  implicit none
  real :: t, sink
  t = -10.0
  sink = -10.0
  call cpu_time(t)
  call require_true('intent out actual overwritten', t /= -10.0 .and. t >= 0.0)
  write(*,'(a)') 'INTRINSICS 16.9.G CPU TIME INTENT OUT ASSIGNMENT OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_cpu_time_intent_out_assignment
