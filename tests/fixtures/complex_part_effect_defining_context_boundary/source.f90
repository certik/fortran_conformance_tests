program complex_part_defining_context_boundary_effect
  implicit none
  complex :: z
  integer :: checks
  checks=0
  z=(3.0, -1.0)
  z%IM=4.0
  if (z%IM /= 4.0) then
    write(*,'(a)') 'CPE:defining_context_boundary:imaginary-assigned'
    error stop
  end if
  checks=checks+1
  if (z%RE /= 3.0) then
    write(*,'(a)') 'CPE:defining_context_boundary:real-unchanged'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CPE:defining_context_boundary:check-total'
    error stop
  end if
  write(*,'(a)') 'COMPLEX PART DEFINING CONTEXT BOUNDARY OK'
end program complex_part_defining_context_boundary_effect
