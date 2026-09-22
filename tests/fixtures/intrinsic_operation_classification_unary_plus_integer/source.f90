! rule: S10.1.5.1-001
! covers: unary-plus-integer
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_unary_plus_integer
  implicit none
  integer :: checks
  integer :: left, right, result
  checks=0
  left = -19
  ! Unary plus preserves the integer operand value; an absolute-value-like result would be 19.
  result = + left
  if (result /= -19) then
    write(*,'(a)') 'IOC:unary_plus_integer:unary-plus-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'IOC:unary_plus_integer:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION UNARY PLUS INTEGER OK'
end program ioc_unary_plus_integer
