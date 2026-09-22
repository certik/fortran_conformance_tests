! rule: S10.1.4-004
! covers: array-left-scalar-right
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_array_left_scalar_right
  implicit none
  integer :: checks
  integer :: a(3), result(3)
  checks=0
  a = [1,4,7]
  ! [1,4,7]-10 = [-9,-6,-3], distinct from 10-array.
  result = a - 10
  if (any(result /= [-9,-6,-3])) then
    write(*,'(a)') 'EOP:array_left_scalar_right:array-left-values'
    error stop
  end if
  checks=checks+1
  if (result(2) /= -6) then
    write(*,'(a)') 'EOP:array_left_scalar_right:array-left-middle'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:array_left_scalar_right:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS ARRAY LEFT SCALAR RIGHT OK'
end program evaluation_operations_array_left_scalar_right
