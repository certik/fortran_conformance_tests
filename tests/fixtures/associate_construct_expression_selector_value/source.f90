! rule: S11.1.3.2-001
! covers: expression-selector-value-before-block
! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.
program associate_construct_expression_selector_value_effect
  implicit none
  integer :: checks
  integer :: seed
  seed=23
  checks=0
  ! seed+17 is evaluated before the block; changing seed later must not change value.
  associate (value => seed + 17)
    seed=-900
  if (value /= 40) then
    write(*,'(a)') 'ACF:expression_selector_value:value-before-block'
    error stop
  end if
  checks=checks+1
  if (seed /= -900) then
    write(*,'(a)') 'ACF:expression_selector_value:operand-changed-control'
    error stop
  end if
  checks=checks+1
  end associate
  if (checks /= 2) then
    write(*,'(a)') 'ACF:expression_selector_value:check-total'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE EXPRESSION SELECTOR VALUE OK'
end program associate_construct_expression_selector_value_effect
