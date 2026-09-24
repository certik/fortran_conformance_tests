program intrinsics_16_9_j_findloc_back_order
  implicit none
  integer :: checks
  integer :: values(4), grid(2,3)
  integer, allocatable :: hit(:)
  checks=0
  values = [2, 6, 4, 6]
  grid = reshape([9, 1, 9, 1, 1, 9], [2,3])
  hit = findloc(values, 6, back=.false.)
  if (any(hit /= [2])) then
    write(*,'(a)') 'I16J:findloc_back_order:back-false-first'
    error stop
  end if
  checks=checks+1
  hit = findloc(values, 6, back=.true.)
  if (any(hit /= [4])) then
    write(*,'(a)') 'I16J:findloc_back_order:back-true-last'
    error stop
  end if
  checks=checks+1
  hit = findloc(grid, 9, back=.true.)
  if (any(hit /= [2, 3])) then
    write(*,'(a)') 'I16J:findloc_back_order:array-element-order'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (3)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC BACK ORDER OK'
end program intrinsics_16_9_j_findloc_back_order
