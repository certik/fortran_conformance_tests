! rule: S10.1.4-004
! covers: scalar-left-array-right
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_scalar_left_array_right
  implicit none
  integer :: checks
  integer :: a(3), result(3)
  checks=0
  a = [1,4,7]
  ! 10-[1,4,7] = [9,6,3].
  result = 10 - a
  if (any(result /= [9,6,3])) then
    write(*,'(a)') 'EOP:scalar_left_array_right:scalar-left-values'
    error stop
  end if
  checks=checks+1
  if (result(2) /= 6) then
    write(*,'(a)') 'EOP:scalar_left_array_right:scalar-left-middle'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:scalar_left_array_right:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS SCALAR LEFT ARRAY RIGHT OK'
end program evaluation_operations_scalar_left_array_right
