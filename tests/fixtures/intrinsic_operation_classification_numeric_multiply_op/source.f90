! rule: S10.1.5.1-003
! covers: numeric-multiply-op
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_numeric_multiply_op
  implicit none
  integer :: checks
  integer :: left, right, result
  checks=0
  left = -6
  right = 7
  ! (-6) * 7 = -42; addition would be 1 and subtraction -13.
  result = left * right
  if (result /= -42) then
    write(*,'(a)') 'IOC:numeric_multiply_op:multiply-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'IOC:numeric_multiply_op:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION NUMERIC MULTIPLY OP OK'
end program ioc_numeric_multiply_op
