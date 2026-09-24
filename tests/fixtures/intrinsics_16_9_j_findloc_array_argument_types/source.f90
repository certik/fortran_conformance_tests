program intrinsics_16_9_j_findloc_array_argument_types
  implicit none
  integer :: checks
  integer :: ints(3)
  character(len=2) :: words(3)
  integer, allocatable :: word_hit(:)
  checks=0
  ints = [9, 2, 4]
  words = ['aa', 'bb', 'cc']
  word_hit = findloc(words, 'bb')
  if (any(word_hit /= [2])) then
    write(*,'(a)') 'I16J:findloc_array_argument_types:character-array'
    error stop
  end if
  checks=checks+1
  word_hit = findloc(ints, 9)
  if (any(word_hit /= [1])) then
    write(*,'(a)') 'I16J:findloc_array_argument_types:integer-array'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC ARRAY ARGUMENT TYPES OK'
end program intrinsics_16_9_j_findloc_array_argument_types
