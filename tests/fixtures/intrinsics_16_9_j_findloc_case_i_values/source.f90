program intrinsics_16_9_j_findloc_case_i_values
  implicit none
  integer :: checks
  integer :: values(4), misses(3)
  integer, allocatable :: empty(:), hit(:)
  checks=0
  values = [2, 6, 4, 6]
  misses = [2, 4, 8]
  allocate(empty(0))
  empty = 6
  hit = findloc(values, 6)
  if (any(hit /= [2])) then
    write(*,'(a)') 'I16J:findloc_case_i_values:matching-subscript'
    error stop
  end if
  checks=checks+1
  hit = findloc(misses, 6)
  if (any(hit /= [0])) then
    write(*,'(a)') 'I16J:findloc_case_i_values:no-match-zero'
    error stop
  end if
  checks=checks+1
  hit = findloc(empty, 6)
  if (any(hit /= [0])) then
    write(*,'(a)') 'I16J:findloc_case_i_values:zero-size-zero'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (3)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC CASE I VALUES OK'
end program intrinsics_16_9_j_findloc_case_i_values
