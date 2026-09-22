! rule: S10.1.4-005
! covers: pure-elemental-function-array-values
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_pure_elemental_function_array_values
  implicit none
  integer :: checks
  integer :: a(3), result(3)
  checks=0
  a = [-2,0,5]
  ! Pure elemental bump maps x to x+3: [1,3,8].
  result = bump(a)
  if (any(result /= [1,3,8])) then
    write(*,'(a)') 'EOP:pure_elemental_function_array_values:pure-elemental-values'
    error stop
  end if
  checks=checks+1
  if (sum(result) /= 12) then
    write(*,'(a)') 'EOP:pure_elemental_function_array_values:pure-elemental-sum'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:pure_elemental_function_array_values:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS PURE ELEMENTAL FUNCTION ARRAY VALUES OK'
contains
  pure elemental integer function bump(x)
    integer, intent(in) :: x
    bump = x + 3
  end function bump
end program evaluation_operations_pure_elemental_function_array_values
