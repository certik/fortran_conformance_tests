program assumed_rank_zero_size_effect
  implicit none
  integer :: a(0), b(0,3)
  integer :: visits, returns, observer_checks, main_checks
  integer :: rank_one_visits, rank_two_visits
  visits=0
  returns=0
  observer_checks=0
  main_checks=0
  rank_one_visits=0
  rank_two_visits=0
  call observe(a, 1, 1)
  returns=returns+1
  call observe(b, 2, 2)
  returns=returns+1
  if (visits /= 2) then
    write(*,'(a)') 'ARE:zero_size:total-visits'
    error stop
  end if
  main_checks=main_checks+1
  if (rank_one_visits /= 1) then
    write(*,'(a)') 'ARE:zero_size:category-1'
    error stop
  end if
  main_checks=main_checks+1
  if (rank_two_visits /= 1) then
    write(*,'(a)') 'ARE:zero_size:category-2'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 2) then
    write(*,'(a)') 'ARE:zero_size:normal-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (observer_checks /= 4) then
    write(*,'(a)') 'ARE:zero_size:observer-checks'
    error stop
  end if
  main_checks=main_checks+1
  if (main_checks /= 5) then
    write(*,'(a)') 'ARE:zero_size:caller-checks'
    error stop
  end if
  write(*,'(a)') 'ASSUMED RANK ZERO SIZE OK'
contains
  subroutine observe(x, expected_rank, expected_visit)
    implicit none
    integer, intent(in) :: x(..)
    integer, intent(in) :: expected_rank, expected_visit
    integer :: observed_rank
    visits=visits+1
    observed_rank=rank(x)
    if (observed_rank /= expected_rank) then
      write(*,'(a,i1)') 'ARE:zero_size:observer-rank:activation=', visits
      error stop
    end if
    observer_checks=observer_checks+1
    if (visits /= expected_visit) then
      write(*,'(a,i1)') 'ARE:zero_size:observer-visit:activation=', visits
      error stop
    end if
    observer_checks=observer_checks+1
    select case (observed_rank)
    case (1)
      rank_one_visits=rank_one_visits+1
    case (2)
      rank_two_visits=rank_two_visits+1
    end select
  end subroutine observe
end program assumed_rank_zero_size_effect
