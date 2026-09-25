program save_common_member_conflict
  implicit none
  integer :: x
  common /shared/ x
  save :: x
end program save_common_member_conflict
