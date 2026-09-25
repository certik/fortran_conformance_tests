program block_save_states
  implicit none
  integer, target :: live
  integer :: iter, checks
  live = 31
  checks = 0
  do iter = 1, 3
    block
      integer, save :: kept
      integer, pointer, save :: p
      integer, pointer, save :: q
      integer, allocatable, save :: a(:), empty(:), never(:)
      if (iter == 1) then
        kept = 11
        p => live
        nullify(q)
        allocate(a(2))
        a = [21, 23]
        if (allocated(never)) error stop
        checks = checks + 1
        allocate(empty(0))
      else if (iter == 2) then
        if (kept /= 11) error stop
        checks = checks + 1
        kept = 17
        live = 37
        if (.not. associated(p, live)) error stop
        checks = checks + 1
        if (p /= 37) error stop
        checks = checks + 1
        if (associated(q)) error stop
        checks = checks + 1
        if (.not. allocated(a)) error stop
        checks = checks + 1
        if (size(a) /= 2) error stop
        checks = checks + 1
        if (a(1) /= 21 .or. a(2) /= 23) error stop
        checks = checks + 1
        a = [27, 29]
        if (allocated(never)) error stop
        checks = checks + 1
        if (.not. allocated(empty)) error stop
        checks = checks + 1
        if (size(empty) /= 0) error stop
        checks = checks + 1
      else
        if (kept /= 17) error stop
        checks = checks + 1
        if (a(1) /= 27 .or. a(2) /= 29) error stop
        checks = checks + 1
        allocate(never(1))
        never = 41
        if (never(1) /= 41) error stop
        checks = checks + 1
        if (.not. allocated(empty)) error stop
        checks = checks + 1
        if (size(empty) /= 0) error stop
        checks = checks + 1
        if (associated(q)) error stop
        checks = checks + 1
      end if
    end block
  end do
  if (checks /= 17) error stop
  print '(a)', 'SAVE BLOCK STATES OK'
end program block_save_states
