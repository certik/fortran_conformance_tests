! rule: S10.1.4-001
! covers: array-intrinsic-element-values
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_array_intrinsic_element_values
  implicit none
  integer :: checks
  integer :: a(3), b(3), result(3)
  checks=0
  a = [8,-3,15]
  b = [2,5,-4]
  ! Element values: [8-2, -3-5, 15-(-4)] = [6,-8,19].
  result = a - b
  if (any(result /= [6,-8,19])) then
    write(*,'(a)') 'EOP:array_intrinsic_element_values:array-subtraction-values'
    error stop
  end if
  checks=checks+1
  if (sum(result) /= 17) then
    write(*,'(a)') 'EOP:array_intrinsic_element_values:array-subtraction-sum'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:array_intrinsic_element_values:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS ARRAY INTRINSIC ELEMENT VALUES OK'
end program evaluation_operations_array_intrinsic_element_values
