program intrinsics_16_9_j_findloc_case_ii_mask
  implicit none
  integer :: checks
  integer :: grid(2,3)
  logical :: select_last(2,3), select_first(2,3), no_match_mask(2,3), false_mask(2,3)
  integer, allocatable :: hit(:)
  checks=0
  grid = reshape([0, 3, 7, 4, 7, 6], [2,3])
  select_last = reshape([.false., .false., .false., .false., .true., .false.], [2,3])
  select_first = reshape([.false., .false., .true., .false., .false., .false.], [2,3])
  no_match_mask = reshape([.true., .true., .false., .true., .false., .true.], [2,3])
  false_mask = .false.
  hit = findloc(grid, 7, mask=select_last)
  if (any(hit /= [1, 3])) then
    write(*,'(a)') 'I16J:findloc_case_ii_mask:masked-match'
    error stop
  end if
  checks=checks+1
  hit = findloc(grid, 7, mask=no_match_mask)
  if (any(hit /= [0, 0])) then
    write(*,'(a)') 'I16J:findloc_case_ii_mask:masked-no-match'
    error stop
  end if
  checks=checks+1
  hit = findloc(grid, 7, mask=false_mask)
  if (any(hit /= [0, 0])) then
    write(*,'(a)') 'I16J:findloc_case_ii_mask:all-false-mask'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (3)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC CASE II MASK OK'
end program intrinsics_16_9_j_findloc_case_ii_mask
