program intrinsics_16_9_j_floor_exact_values
  implicit none
  integer :: checks
  integer :: pos, neg, exact
  checks=0
  pos = floor(3.75)
  if (pos /= 3) then
    write(*,'(a)') 'I16J:floor_exact_values:positive-fraction'
    error stop
  end if
  checks=checks+1
  neg = floor(-3.25)
  if (neg /= -4) then
    write(*,'(a)') 'I16J:floor_exact_values:negative-fraction'
    error stop
  end if
  checks=checks+1
  exact = floor(-3.0)
  if (exact /= -3) then
    write(*,'(a)') 'I16J:floor_exact_values:exact-integer'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (3)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FLOOR EXACT VALUES OK'
end program intrinsics_16_9_j_floor_exact_values
