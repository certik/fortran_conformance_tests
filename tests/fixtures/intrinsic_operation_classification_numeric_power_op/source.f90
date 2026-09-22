! rule: S10.1.5.1-003
! covers: numeric-power-op
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_numeric_power_op
  implicit none
  integer :: checks
  integer :: left, right, result
  checks=0
  left = 2
  right = 5
  ! 2 ** 5 = 32; multiplication would be 10.
  result = left ** right
  if (result /= 32) then
    write(*,'(a)') 'IOC:numeric_power_op:power-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'IOC:numeric_power_op:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION NUMERIC POWER OP OK'
end program ioc_numeric_power_op
