program intrinsics_16_9_j_findloc_transformational_class
  implicit none
  integer :: checks
  integer :: grid(2,2)
  checks=0
  grid = reshape([1, 5, 5, 9], [2,2])
  if (size(findloc(grid, 5)) /= rank(grid)) then
    write(*,'(a)') 'I16J:findloc_transformational_class:whole-array-transform'
    error stop
  end if
  checks=checks+1
  if (any(findloc(grid, 5) /= [2, 1])) then
    write(*,'(a)') 'I16J:findloc_transformational_class:subscript-vector'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC TRANSFORMATIONAL CLASS OK'
end program intrinsics_16_9_j_findloc_transformational_class
