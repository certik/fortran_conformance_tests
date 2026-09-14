program integer_literal_profile
    implicit none
    integer, parameter :: candidate = kind(0)
    integer, parameter :: k = candidate
    integer(k) :: limit, reconstructed
    integer :: i
    if (candidate < 0) error stop 1
    if (radix(0_k) /= 2) stop 77
    if (digits(0_k) /= 31) stop 77
    limit = huge(0_k)
    reconstructed = 0_k
    do i = 1, 31
        if (reconstructed > (limit - 1_k) / 2_k) error stop 2
        reconstructed = 2_k * reconstructed + 1_k
    end do
    if (reconstructed /= limit) error stop 3
    print *, 'kind_radix_digits_range', k, radix(0_k), digits(0_k), range(0_k)
    print *, 'model_limit', limit
end program
