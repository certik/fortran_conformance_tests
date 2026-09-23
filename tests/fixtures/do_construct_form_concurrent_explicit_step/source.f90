! rule: R1126
! covers: concurrent-control-explicit-step
program do_construct_form_concurrent_explicit_step
  implicit none
  integer :: trace(5)
  integer :: i
  trace = -777
  do concurrent (i = 1:5:2)
    trace(i) = 10 + i
  end do
  if (any(trace /= [11, -777, 13, -777, 15])) then
    write(*,'(a)') 'DCF:do_construct_form_concurrent_explicit_step:trace'
    error stop
  end if
  if (trace(2) /= -777) then
    write(*,'(a)') 'DCF:explicit-step:sentinel-two'
    error stop
  end if
  if (trace(4) /= -777) then
    write(*,'(a)') 'DCF:explicit-step:sentinel-four'
    error stop
  end if
  if (count(trace /= -777) /= 3) then
    write(*,'(a)') 'DCF:do_construct_form_concurrent_explicit_step:count'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM CONCURRENT EXPLICIT STEP OK'
end program do_construct_form_concurrent_explicit_step
