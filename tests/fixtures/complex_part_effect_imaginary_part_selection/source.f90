program complex_part_imaginary_part_selection_effect
  implicit none
  complex :: z
  integer :: checks
  checks=0
  z=(7.0, -2.0)
  if (z%IM /= -2.0) then
    write(*,'(a)') 'CPE:imaginary_part_selection:imaginary-selected'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'CPE:imaginary_part_selection:check-total'
    error stop
  end if
  write(*,'(a)') 'COMPLEX PART IMAGINARY PART SELECTION OK'
end program complex_part_imaginary_part_selection_effect
