program complex_part_real_part_selection_effect
  implicit none
  complex :: z
  integer :: checks
  checks=0
  z=(7.0, -2.0)
  if (z%RE /= 7.0) then
    write(*,'(a)') 'CPE:real_part_selection:real-selected'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'CPE:real_part_selection:check-total'
    error stop
  end if
  write(*,'(a)') 'COMPLEX PART REAL PART SELECTION OK'
end program complex_part_real_part_selection_effect
