! rule: S10.1.5.1-003
! covers: numeric-add-op
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_numeric_add_op
  implicit none
  integer :: checks
  integer :: left, right, result
  checks=0
  left = 14
  right = -5
  ! 14 + (-5) = 9; subtraction would be 19 and multiplication -70.
  result = left + right
  if (result /= 9) then
    write(*,'(a)') 'IOC:numeric_add_op:add-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'IOC:numeric_add_op:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION NUMERIC ADD OP OK'
end program ioc_numeric_add_op
