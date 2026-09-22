! rule: S8.4-005
! covers: data-part-retention
! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.
program initialization_data_part_retention_effect
  implicit none
  integer :: first_a, first_b, second_a, second_b, checks
  checks=0
  call visit(1, first_a, first_b)
  call visit(2, second_a, second_b)
  if (first_a /= -12345) then
    write(*,'(a)') 'INIT:data_part_retention:first-initialized-part'
    error stop
  end if
  checks=checks+1
  if (first_b /= 2468) then
    write(*,'(a)') 'INIT:data_part_retention:first-defined-other-part'
    error stop
  end if
  checks=checks+1
  if (second_a /= -12344) then
    write(*,'(a)') 'INIT:data_part_retention:second-retained-initialized-part'
    error stop
  end if
  checks=checks+1
  if (second_b /= 2468) then
    write(*,'(a)') 'INIT:data_part_retention:second-retained-other-part'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'INIT:data_part_retention:check-total'
    error stop
  end if
  write(*,'(a)') 'INITIALIZATION DATA PART RETENTION OK'
contains
  subroutine visit(pass, obs_a, obs_b)
    implicit none
    integer, intent(in) :: pass
    integer, intent(out) :: obs_a, obs_b
    integer :: a(-2:-1)
    data a(-2) /-12345/
    if (lbound(a,1) /= -2) error stop
    if (ubound(a,1) /= -1) error stop
    if (pass == 1) then
      a(-1) = 2468
      obs_a = a(-2)
      obs_b = a(-1)
      a(-2) = -12344
    else
      obs_a = a(-2)
      obs_b = a(-1)
    end if
  end subroutine visit
end program initialization_data_part_retention_effect
