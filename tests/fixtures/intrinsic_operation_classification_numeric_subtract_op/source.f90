! rule: S10.1.5.1-003
! covers: numeric-subtract-op
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_numeric_subtract_op
  implicit none
  integer :: checks
  integer :: left, right, result
  checks=0
  left = 14
  right = -5
  ! 14 - (-5) = 19; addition would be 9.
  result = left - right
  if (result /= 19) then
    write(*,'(a)') 'IOC:numeric_subtract_op:subtract-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'IOC:numeric_subtract_op:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION NUMERIC SUBTRACT OP OK'
end program ioc_numeric_subtract_op
