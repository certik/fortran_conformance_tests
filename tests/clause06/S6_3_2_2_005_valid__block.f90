! rule: S6.3.2.2-005
! covers: end-block
! evidence: positive-control
program block_spellings
  implicit none
  integer :: value
  block
    integer :: local
    local = 11
    value = local
  endblock
  if (value /= 11) stop 1
  block
    integer :: local
    local = 12
    value = local
  end block
  if (value /= 12) stop 2
end program
