program complex_part_array_shape_inherited_effect
  implicit none
  complex :: a(3)
  integer :: checks
  checks=0
  a(1)=(1.0, 0.5)
  a(2)=(-2.0, 1.25)
  a(3)=(4.0, -0.25)
  if (size(a%RE) /= 3) then
    write(*,'(a)') 'CPE:array_shape_inherited:real-size'
    error stop
  end if
  checks=checks+1
  if (sum(a%IM) /= 1.5) then
    write(*,'(a)') 'CPE:array_shape_inherited:imaginary-sum'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CPE:array_shape_inherited:check-total'
    error stop
  end if
  write(*,'(a)') 'COMPLEX PART ARRAY SHAPE INHERITED OK'
end program complex_part_array_shape_inherited_effect
