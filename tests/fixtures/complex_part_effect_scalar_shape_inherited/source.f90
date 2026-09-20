program complex_part_scalar_shape_inherited_effect
  implicit none
  complex :: z
  real :: selected
  integer :: checks
  checks=0
  z=(5.0, -6.0)
  selected=-8.0
  selected=z%RE
  if (selected /= 5.0) then
    write(*,'(a)') 'CPE:scalar_shape_inherited:scalar-selected'
    error stop
  end if
  checks=checks+1
  if (checks /= 1) then
    write(*,'(a)') 'CPE:scalar_shape_inherited:check-total'
    error stop
  end if
  write(*,'(a)') 'COMPLEX PART SCALAR SHAPE INHERITED OK'
end program complex_part_scalar_shape_inherited_effect
