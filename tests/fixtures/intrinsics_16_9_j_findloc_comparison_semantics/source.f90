program intrinsics_16_9_j_findloc_comparison_semantics
  implicit none
  integer :: checks
  logical :: flags(4)
  character(len=2) :: words(3)
  integer, allocatable :: hit(:)
  checks=0
  flags = [.false., .true., .true., .false.]
  words = ['aa', 'bb', 'aa']
  hit = findloc(flags, .true.)
  if (any(hit /= [2])) then
    write(*,'(a)') 'I16J:findloc_comparison_semantics:logical-eqv'
    error stop
  end if
  checks=checks+1
  hit = findloc(words, 'bb')
  if (any(hit /= [2])) then
    write(*,'(a)') 'I16J:findloc_comparison_semantics:nonlogical-equality'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC COMPARISON SEMANTICS OK'
end program intrinsics_16_9_j_findloc_comparison_semantics
