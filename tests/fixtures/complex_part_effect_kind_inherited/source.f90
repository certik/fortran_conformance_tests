program complex_part_kind_inherited_effect
  implicit none
  complex(kind(0.0d0)) :: z
  integer :: checks
  checks=0
  z=(3.0d0, -4.0d0)
  if (kind(z%RE) /= kind(z)) then
    write(*,'(a)') 'CPE:kind_inherited:real-kind'
    error stop
  end if
  checks=checks+1
  if (kind(z%IM) /= kind(z)) then
    write(*,'(a)') 'CPE:kind_inherited:imaginary-kind'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CPE:kind_inherited:check-total'
    error stop
  end if
  write(*,'(a)') 'COMPLEX PART KIND INHERITED OK'
end program complex_part_kind_inherited_effect
