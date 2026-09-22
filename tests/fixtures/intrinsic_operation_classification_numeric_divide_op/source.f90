! rule: S10.1.5.1-003
! covers: numeric-divide-op
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_numeric_divide_op
  implicit none
  integer :: checks
  integer :: left, right, result
  checks=0
  left = 17
  right = 5
  ! Integer division 17 / 5 gives 3; real division would be 3.4 and fail this direct expression guard.
  if (left / right /= 3) then
    write(*,'(a)') 'IOC:numeric_divide_op:divide-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'IOC:numeric_divide_op:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION NUMERIC DIVIDE OP OK'
end program ioc_numeric_divide_op
