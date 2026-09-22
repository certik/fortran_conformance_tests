! rule: S10.1.4-003
! covers: nested-implied-do-controls
! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.
program evaluation_operations_nested_implied_do_controls
  implicit none
  integer :: checks
  integer :: i, j
  integer :: result(4)
  checks=0
  result = [((10*i+j, i=2-1, 3, 1+1), j=1+2, 4+1, 1+1)]
  ! Inner i values are 1,3 and outer j values are 3,5: [13,33,15,35].
  if (any(result /= [13,33,15,35])) then
    write(*,'(a)') 'EOP:nested_implied_do_controls:nested-values'
    error stop
  end if
  checks=checks+1
  if (size(result) /= 4) then
    write(*,'(a)') 'EOP:nested_implied_do_controls:nested-size'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'EOP:nested_implied_do_controls:check-total'
    error stop
  end if
  write(*,'(a)') 'EVALUATION OPERATIONS NESTED IMPLIED DO CONTROLS OK'
end program evaluation_operations_nested_implied_do_controls
