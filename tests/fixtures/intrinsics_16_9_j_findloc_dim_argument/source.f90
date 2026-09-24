program intrinsics_16_9_j_findloc_dim_argument
  implicit none
  integer :: checks
  integer :: grid(2,3)
  integer, allocatable :: dim_hit(:)
  checks=0
  grid = reshape([1, 2, 2, 3, 4, 2], [2,3])
  dim_hit = findloc(grid, 2, dim=1)
  if (any(dim_hit /= [2, 1, 2])) then
    write(*,'(a)') 'I16J:findloc_dim_argument:dim-one-in-range'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC DIM ARGUMENT OK'
end program intrinsics_16_9_j_findloc_dim_argument
