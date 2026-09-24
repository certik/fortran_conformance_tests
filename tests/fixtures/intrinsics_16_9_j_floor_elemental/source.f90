program intrinsics_16_9_j_floor_elemental
  implicit none
  integer :: checks
  real :: values(3)
  integer :: observed(3)
  checks=0
  values = [3.75, -3.25, -3.0]
  observed = floor(values)
  if (any(observed /= [3, -4, -3])) then
    write(*,'(a)') 'I16J:floor_elemental:elementwise-values'
    error stop
  end if
  checks=checks+1
  if (any(shape(floor(values)) /= [3])) then
    write(*,'(a)') 'I16J:floor_elemental:elementwise-shape'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FLOOR ELEMENTAL OK'
end program intrinsics_16_9_j_floor_elemental
