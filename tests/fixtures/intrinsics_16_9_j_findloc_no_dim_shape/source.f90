program intrinsics_16_9_j_findloc_no_dim_shape
  implicit none
  integer :: checks
  integer :: vector(3), grid(2,3)
  checks=0
  vector = [2, 6, 4]
  grid = reshape([1, 2, 2, 3, 4, 2], [2,3])
  if (size(shape(findloc(vector, 6))) /= 1) then
    write(*,'(a)') 'I16J:findloc_no_dim_shape:rank-one-result'
    error stop
  end if
  checks=checks+1
  if (size(findloc(grid, 2)) /= rank(grid)) then
    write(*,'(a)') 'I16J:findloc_no_dim_shape:size-equals-array-rank'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC NO DIM SHAPE OK'
end program intrinsics_16_9_j_findloc_no_dim_shape
