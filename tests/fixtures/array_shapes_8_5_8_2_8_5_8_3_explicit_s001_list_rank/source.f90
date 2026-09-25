module explicit_s001_rank_module
  implicit none
  integer :: module_rank_two(2,3)
end module explicit_s001_rank_module
program explicit_s001_list_rank
  use explicit_s001_rank_module
  implicit none
  integer :: main_rank_two(2,3)
  integer :: zero_extent(0,3)
  if (rank(module_rank_two) /= 2) error stop 'S001 module rank'
  if (rank(main_rank_two) /= 2) error stop 'S001 main rank'
  if (rank(zero_extent) /= 2) error stop 'S001 zero extent rank'
  write(*,'(a)') 'ARRAY SHAPES EXPLICIT S001 OK'
end program explicit_s001_list_rank
