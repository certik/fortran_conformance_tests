program intrinsics_16_9_b_any_or_reduction
  implicit none
  integer :: checks
  logical :: mask(3), observed, explicit_or
  checks=0
  mask = [.false., .true., .false.]
  observed = any(mask)
  explicit_or = mask(1) .or. mask(2) .or. mask(3)
  if (observed .neqv. explicit_or) then
    write(*,'(a)') 'I16B:any_or_reduction:or-reduction'
    error stop
  end if
  checks=checks+1
  if (.not. observed) then
    write(*,'(a)') 'I16B:any_or_reduction:true-result'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16B:any_or_reduction:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ANY OR REDUCTION OK'
end program intrinsics_16_9_b_any_or_reduction
