! rule: R1128
! covers: concurrent-step-expression-form
program do_construct_form_concurrent_step_expression
  implicit none
  integer :: trace(5)
  integer :: i
  integer :: step
  trace = -777
  step = 2
  do concurrent (i = 1:5:step)
    trace(i) = 10 + i
  end do
  if (any(trace /= [11, -777, 13, -777, 15])) then
    write(*,'(a)') 'DCF:do_construct_form_concurrent_step_expression:trace'
    error stop
  end if
  if (trace(2) /= -777) then
    write(*,'(a)') 'DCF:step-expression:sentinel-two'
    error stop
  end if
  if (trace(4) /= -777) then
    write(*,'(a)') 'DCF:step-expression:sentinel-four'
    error stop
  end if
  if (count(trace /= -777) /= 3) then
    write(*,'(a)') 'DCF:do_construct_form_concurrent_step_expression:count'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM CONCURRENT STEP EXPRESSION OK'
end program do_construct_form_concurrent_step_expression
