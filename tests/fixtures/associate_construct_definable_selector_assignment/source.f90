! rule: S11.1.3.3-005
! covers: definable-selector-assignment-control
! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.
program associate_construct_definable_selector_assignment_effect
  implicit none
  integer :: checks
  integer :: store(5:9)
  store=[50,60,70,80,90]
  checks=0
  ! The triplet section store(6:8) is definable and has no vector subscript.
  associate (vec => store(6:8))
    vec=[601,602,603]
  end associate
  if (store(6) /= 601) then
    write(*,'(a)') 'ACF:definable_selector_assignment:first-selector-element'
    error stop
  end if
  checks=checks+1
  if (store(7) /= 602) then
    write(*,'(a)') 'ACF:definable_selector_assignment:middle-selector-element'
    error stop
  end if
  checks=checks+1
  if (store(8) /= 603) then
    write(*,'(a)') 'ACF:definable_selector_assignment:last-selector-element'
    error stop
  end if
  checks=checks+1
  if (store(5) /= 50) then
    write(*,'(a)') 'ACF:definable_selector_assignment:neighbor-unchanged'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'ACF:definable_selector_assignment:check-total'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE DEFINABLE SELECTOR ASSIGNMENT OK'
end program associate_construct_definable_selector_assignment_effect
