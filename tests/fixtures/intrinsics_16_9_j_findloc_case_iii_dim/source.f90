program intrinsics_16_9_j_findloc_case_iii_dim
  implicit none
  integer :: checks
  integer :: vector(3), grid(2,3), scalar_hit
  integer, allocatable :: dim_hit(:)
  checks=0
  vector = [2, 6, 4]
  grid = reshape([1, 2, 2, 2, -9, 6], [2,3])
  scalar_hit = findloc(vector, 6, dim=1)
  if (scalar_hit /= 2) then
    write(*,'(a)') 'I16J:findloc_case_iii_dim:rank-one-dim-scalar'
    error stop
  end if
  checks=checks+1
  dim_hit = findloc(grid, 2, dim=1)
  if (any(dim_hit /= [2, 1, 0])) then
    write(*,'(a)') 'I16J:findloc_case_iii_dim:section-wise-dim'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC CASE III DIM OK'
end program intrinsics_16_9_j_findloc_case_iii_dim
