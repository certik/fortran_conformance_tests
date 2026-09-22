! rule: S11.1.3.2-002
! covers: associate-name-defines-variable-selector
! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.
program associate_construct_variable_selector_define_effect
  implicit none
  integer :: checks
  integer :: target
  target=314
  checks=0
  ! alias identifies target, so defining alias in the block changes target.
  associate (alias => target)
    alias=271
  end associate
  if (target /= 271) then
    write(*,'(a)') 'ACF:variable_selector_define:selector-defined'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'ACF:variable_selector_define:check-total'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE VARIABLE SELECTOR DEFINE OK'
end program associate_construct_variable_selector_define_effect
