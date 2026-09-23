! rule: R1126
! covers: concurrent-control-default-step
program do_construct_form_concurrent_default_step
  implicit none
  integer :: trace(4)
  integer :: i
  trace = -777
  do concurrent (i = 1:4)
    trace(i) = 10 + i
  end do
  if (any(trace /= [11, 12, 13, 14])) then
    write(*,'(a)') 'DCF:do_construct_form_concurrent_default_step:trace'
    error stop
  end if
  if (count(trace /= -777) /= 4) then
    write(*,'(a)') 'DCF:do_construct_form_concurrent_default_step:count'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM CONCURRENT DEFAULT STEP OK'
end program do_construct_form_concurrent_default_step
