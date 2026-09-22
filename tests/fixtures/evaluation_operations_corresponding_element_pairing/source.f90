! rule: S10.1.4-004
! covers: corresponding-element-pairing
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_corresponding_element_pairing
  implicit none
  integer :: checks
  integer :: a(3), b(3), result(3)
  checks=0
  a = [1,100,7]
  b = [10,1,-5]
  ! Pairwise subtraction gives [1-10,100-1,7-(-5)] = [-9,99,12].
  result = a - b
  if (any(result /= [-9,99,12])) then
    write(*,'(a)') 'EOP:corresponding_element_pairing:corresponding-values'
    error stop
  end if
  checks=checks+1
  if (result(2) /= 99) then
    write(*,'(a)') 'EOP:corresponding_element_pairing:corresponding-middle'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:corresponding_element_pairing:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS CORRESPONDING ELEMENT PAIRING OK'
end program evaluation_operations_corresponding_element_pairing
