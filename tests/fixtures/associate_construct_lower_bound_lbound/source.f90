! rule: S11.1.3.3-001
! covers: nondefault-lower-bound
! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.
program associate_construct_lower_bound_lbound_effect
  implicit none
  integer :: checks
  integer :: base(-5:5)
  integer :: whole_lower, section_lower
  base=0
  checks=0
  ! Whole-array LBOUND is -5; section base(-3:3:2) has LBOUND result 1.
  associate (whole => base)
    whole_lower=lbound(whole,1)
  end associate
  associate (sec => base(-3:3:2))
    section_lower=lbound(sec,1)
  end associate
  if (whole_lower /= -5) then
    write(*,'(a)') 'ACF:lower_bound_lbound:whole-nondefault-lower'
    error stop
  end if
  checks=checks+1
  if (section_lower /= 1) then
    write(*,'(a)') 'ACF:lower_bound_lbound:section-lbound-result'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'ACF:lower_bound_lbound:check-total'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE LOWER BOUND LBOUND OK'
end program associate_construct_lower_bound_lbound_effect
